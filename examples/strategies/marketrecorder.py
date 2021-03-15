import os
import json
import time
import logging
import zipfile
import boto3
from boto3.s3.transfer import S3Transfer, TransferConfig
from botocore.exceptions import BotoCoreError

from flumine import BaseStrategy
from flumine.utils import create_short_uuid, file_line_count

logger = logging.getLogger(__name__)


class MarketRecorder(BaseStrategy):

    MARKET_ID_LOOKUP = "id"

    def __init__(self, *args, **kwargs):
        BaseStrategy.__init__(self, *args, **kwargs)
        self._market_expiration = self.context.get("market_expiration", 3600)  # seconds
        self._remove_file = self.context.get(
            "remove_file", True
        )  # remove txt file after zip
        self._force_update = self.context.get(
            "force_update", True
        )  # update after initial closure
        self.local_dir = self.context.get("local_dir", "/tmp")
        self.recorder_id = create_short_uuid()
        self._loaded_markets = []  # list of marketIds

    def add(self) -> None:
        logger.info("Adding strategy %s with id %s" % (self.name, self.recorder_id))
        # check local dir
        if not os.path.isdir(self.local_dir):
            raise OSError("File dir %s does not exist" % self.local_dir)
        # create sub dir
        directory = os.path.join(self.local_dir, self.recorder_id)
        if not os.path.exists(directory):
            os.makedirs(directory)

    def process_raw_data(self, publish_time, data):
        market_id = data.get(self.MARKET_ID_LOOKUP)
        file_directory = os.path.join(self.local_dir, self.recorder_id, market_id)
        with open(file_directory, "a") as f:
            f.write(
                json.dumps({"op": "mcm", "clk": None, "pt": publish_time, "mc": [data]})
                + "\n"
            )

    def process_closed_market(self, market, data: dict) -> None:
        market_id = data.get(self.MARKET_ID_LOOKUP)
        if market_id in self._loaded_markets:
            if self._force_update:
                logger.warning(
                    "File: /{0}/{1}/{2} has already been loaded, updating..".format(
                        self.local_dir, self.recorder_id, market_id
                    )
                )
            else:
                return
        logger.info("Closing market %s" % market_id)

        file_dir = os.path.join(self.local_dir, self.recorder_id, market_id)
        market_definition = data.get("marketDefinition")

        # check that file actually exists
        if not os.path.isfile(file_dir):
            logger.error(
                "File: %s does not exist in /%s/%s/"
                % (self.local_dir, market_id, self.recorder_id)
            )
            return

        # check that file is not empty / 1 line (i.e. the market had already closed on startup)
        line_count = file_line_count(file_dir)
        if line_count == 1:
            logger.warning(
                "File: %s contains one line only and will not be loaded (already closed on startup)"
                % file_dir
            )
            return

        # zip file
        zip_file_dir = self._zip_file(file_dir, market_id)

        # core load code
        self._load(market, zip_file_dir, market_definition)

        # clean up
        self._clean_up()

        self._loaded_markets.append(market_id)

    def _zip_file(self, file_dir: str, market_id: str) -> str:
        """zips txt file into filename.zip"""
        zip_file_directory = os.path.join(
            self.local_dir, self.recorder_id, "%s.zip" % market_id
        )
        with zipfile.ZipFile(zip_file_directory, mode="w") as zf:
            zf.write(
                file_dir, os.path.basename(file_dir), compress_type=zipfile.ZIP_DEFLATED
            )
        return zip_file_directory

    def _load(self, market, zip_file_dir: str, market_definition: dict) -> None:
        pass

    def _clean_up(self) -> None:
        """If zip > market_expiration old remove
        zip and txt file
        """
        directory = os.path.join(self.local_dir, self.recorder_id)
        for file in os.listdir(directory):
            if file.endswith(".zip"):
                file_stats = os.stat(os.path.join(directory, file))
                seconds_since = time.time() - file_stats.st_mtime
                if seconds_since > self._market_expiration:
                    logger.info(
                        "Removing: %s, age: %ss" % (file, round(seconds_since, 2))
                    )
                    txt_path = os.path.join(directory, file.split(".zip")[0])
                    zip_path = os.path.join(directory, file)
                    os.remove(zip_path)
                    if self._remove_file:
                        os.remove(txt_path)

    @staticmethod
    def _create_metadata(market_definition: dict) -> dict:
        try:
            del market_definition["runners"]
        except KeyError:
            pass
        return dict([a, str(x)] for a, x in market_definition.items())


class S3MarketRecorder(MarketRecorder):
    def __init__(self, *args, **kwargs):
        MarketRecorder.__init__(self, *args, **kwargs)
        self._bucket = self.context["bucket"]
        self._data_type = self.context.get("data_type", "marketdata")
        self.s3 = boto3.client("s3")
        transfer_config = TransferConfig(use_threads=False)
        self.transfer = S3Transfer(self.s3, config=transfer_config)

    def add(self) -> None:
        super().add()
        self.s3.head_bucket(Bucket=self._bucket)  # validate bucket/access

    def _load(self, market, zip_file_dir: str, market_definition: dict) -> None:
        # note this will block the main handler queue during upload
        # todo create background worker instead?
        event_type_id = (
            market_definition.get("eventTypeId", 0) if market_definition else "7"
        )
        try:
            self.transfer.upload_file(
                filename=zip_file_dir,
                bucket=self._bucket,
                key=os.path.join(
                    self._data_type,
                    "streaming",
                    event_type_id,
                    os.path.basename(zip_file_dir),
                ),
                extra_args={
                    "Metadata": self._create_metadata(market_definition)
                    if market_definition
                    else {}
                },
            )
            logger.info("%s successfully loaded to s3" % zip_file_dir)
        except (BotoCoreError, Exception) as e:
            logger.error("Error loading to s3: %s" % e)

        # upload marketCatalogue data
        if market and self.context.get("load_market_catalogue", True):
            if market.market_catalogue is None:
                logger.warning(
                    "No marketCatalogue data available for %s" % market.market_id
                )
                return
            try:
                self.s3.put_object(
                    Body=market.market_catalogue.json(),
                    Bucket=self._bucket,
                    Key=os.path.join(
                        "marketdata",
                        "marketCatalogue",
                        market.market_id,
                    ),
                )
                logger.info(
                    "%s successfully loaded marketCatalogue to s3" % market.market_id
                )
            except (BotoCoreError, Exception) as e:
                logger.error("Error loading to s3: %s" % e)
