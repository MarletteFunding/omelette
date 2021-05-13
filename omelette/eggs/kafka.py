import json
from datetime import datetime
from enum import Enum
from ssl import create_default_context, SSLContext
from tempfile import NamedTemporaryFile
from typing import Dict, Any, Optional, List
from uuid import uuid4

from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from kafka import KafkaConsumer, KafkaProducer


class KafkaMessageSpecEnum(Enum):
    JSON_SCHEMA = "JSON_SCHEMA"
    CLOUDEVENTS = "CLOUDEVENTS"
    NONE = "NONE"


class Kafka:
    # TODO: add more types
    JSON_TYPE_MAP = {
        str: "string",
    }

    def __init__(self, bootstrap_servers: str, security_protocol: Optional[str] = None,
                 keystore_location: Optional[str] = None, keystore_password: Optional[str] = None,
                 auto_offset_reset: Optional[str] = "latest"):
        self.bootstrap_servers = bootstrap_servers
        self.security_protocol = security_protocol
        self.keystore_location = keystore_location
        self.keystore_password = keystore_password
        self.auto_offset_reset = auto_offset_reset
        self.ssl_context = self.get_ssl_context() if self.security_protocol == "SSL" else None
        self.consumer: Optional[KafkaConsumer] = None
        self._producer: Optional[KafkaProducer] = None

    def get_consumer(self, topic: str, group_id: str) -> KafkaConsumer:
        self.consumer = KafkaConsumer(
            topic,
            group_id=group_id,
            bootstrap_servers=self.bootstrap_servers,
            security_protocol=self.security_protocol,
            ssl_context=self.ssl_context,
            auto_offset_reset=self.auto_offset_reset
        )
        return self.consumer

    @property
    def producer(self) -> KafkaProducer:
        if not self._producer:
            self._producer = KafkaProducer(bootstrap_servers=self.bootstrap_servers,
                                           security_protocol=self.security_protocol,
                                           ssl_context=self.ssl_context,
                                           value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        return self._producer

    def send_message(self, topic: str, value: Dict[str, Any], key: Optional[Dict[str, Any]] = None,
                     spec: Optional[KafkaMessageSpecEnum] = KafkaMessageSpecEnum.NONE, message_type: Optional[str] = None,
                     json_schema_fields: Optional[List[Dict[Any, Any]]] = None, infer_json_schema: bool = False):
        if spec == KafkaMessageSpecEnum.JSON_SCHEMA:
            value = self.map_to_json_schema(value, json_schema_fields, infer_json_schema)
        elif spec == KafkaMessageSpecEnum.CLOUDEVENTS:
            if not message_type:
                raise Exception("Field `message_type` required for Cloudevents spec. Example: 'com.marlette.v1.events.account.AccountCreatedEvent")
            value = self.map_to_cloudevents(value, message_type)

        self.producer.send(topic=topic, value=value, key=key)

    def get_ssl_context(self) -> SSLContext:
        with open(self.keystore_location, "rb") as f:
            pkey, certificate, additional_certs = pkcs12.load_key_and_certificates(
                f.read(),
                bytes(self.keystore_password, encoding="utf-8")
            )

        key = NamedTemporaryFile()
        cert = NamedTemporaryFile()
        key.write(
            pkey.private_bytes(
                encoding=Encoding.PEM,
                format=PrivateFormat.PKCS8,
                encryption_algorithm=NoEncryption(),
            )
        )
        key.flush()
        cert.write(
            certificate.public_bytes(Encoding.PEM),
        )
        cert.flush()

        ssl_context = create_default_context()
        ssl_context.load_cert_chain(certfile=cert.name, keyfile=key.name)

        return ssl_context

    @staticmethod
    def map_to_cloudevents(message: Dict[Any, Any], message_type: str) -> Dict[Any, Any]:
        return {
            "id": str(uuid4()),
            "source": "/omelette/kafka",
            "subject": None,
            "specversion": "1.0",
            "type": message_type,
            "time": datetime.utcnow().isoformat(),
            "datacontenttype": "application/json",
            "dataschema": None,
            "data": message
        }

    def _infer_json_fields(self, message: Dict[Any, Any]) -> List[Dict[str, Any]]:
        schema_fields = []

        for k, v in message.items():
            schema_fields.append({
                "field": k,
                "type": self.JSON_TYPE_MAP.get(type(v)),
                "optional": True
            })

        return schema_fields

    def map_to_json_schema(self, message: Dict[Any, Any], schema_fields: Optional[List[Dict[Any, Any]]] = None,
                           infer: bool = False) -> Dict[Any, Any]:
        if not schema_fields and infer:
            schema_fields = self._infer_json_fields(message)

        return {
            "schema": {
                "$schema": "http://json-schema.org/draft-04/schema#",
                "type": "struct",
                "fields": schema_fields
            },
            "payload": message
        }
