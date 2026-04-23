#!/usr/bin/env python
from dataclasses import dataclass
from typing import List, Optional

import json
import os
import yaml


@dataclass
class Config:
    input_dir: str
    output_dir: str
    def get_labels_file_path(self) -> str:
        return os.path.join(self.input_dir, "labels.json")


@dataclass
class LabelDescr:
    id: str
    path: str
    parent_id: str
    name: str
    color: str
    kind: int

    @staticmethod
    def from_dict(d: dict) -> 'LabelDescr':
        return LabelDescr(
            id=d.get("ID", ""),
            path=d.get("Path", ""),
            parent_id=d.get("ParentID", ""),
            name=d.get("Name", ""),
            color=d.get("Color", ""),
            kind=d.get("Type", 0),
        )


    @staticmethod
    def load(config: Config) -> List['LabelDescr']:
        labels = []
        path = config.get_labels_file_path()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("Payload", []):
                labels.append(LabelDescr.from_dict(item))
        return labels


class Folder:
    def __init__(self, label: LabelDescr, path: str):
        self.label = label
        self.path = path
        self.count: int = 0


    def create(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path)
            print(f"Created folder: {self.path}")
        else:
            print(f"Folder already exists: {self.path}")


    @staticmethod
    def setup(config: Config, labels: List[LabelDescr]) -> List['Folder']:
        folders = []
        create = set()
        exclude = set()
        if config.folders_config:
            if not os.path.exists(config.folders_config):
                raise FileNotFoundError(f"Folder config file not found: {config.folders_config}")
            with open(config.folders_config, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if "create" in data:
                    create = set(data["create"])
                if "exclude" in data:
                    exclude = set(data["exclude"])
        for label in labels:
            if (not label.id.isdigit() or label.id in create) and not (label.id in exclude or label.name in exclude):
                print(f"Creating folder for label '{label.name}' (ID: {label.id})")
                folder = Folder(label, os.path.join(config.output_dir, label.name))
                folders.append(folder)
        return folders


@dataclass
class MessageMeta:
    id: str
    address_id: str
    label_ids: List[str]
    external_id: str
    subject: str
    sender_name: str
    sender_address: str
    to_list: List[dict]
    cc_list: List[dict]
    bcc_list: List[dict]
    reply_tos: List[dict]
    flags: int
    time: int
    size: int
    unread: int
    is_replied: int
    is_replied_all: int
    is_forwarded: int
    num_attachments: int
    attachments: List[dict]
    mime_type: str
    headers: str
    writer_type: int

    @staticmethod
    def from_dict(d: dict) -> 'MessageMeta':
        return MessageMeta(
            id=d.get("ID", ""),
            address_id=d.get("AddressID", ""),
            label_ids=d.get("LabelIDs", []),
            external_id=d.get("ExternalID", ""),
            subject=d.get("Subject", ""),
            sender_name=d.get("Sender", {}).get("Name", ""),
            sender_address=d.get("Sender", {}).get("Address", ""),
            to_list=d.get("ToList", []),
            cc_list=d.get("CCList", []),
            bcc_list=d.get("BCCList", []),
            reply_tos=d.get("ReplyTos", []),
            flags=d.get("Flags", 0),
            time=d.get("Time", 0),
            size=d.get("Size", 0),
            unread=d.get("Unread", 0),
            is_replied=d.get("IsReplied", 0),
            is_replied_all=d.get("IsRepliedAll", 0),
            is_forwarded=d.get("IsForwarded", 0),
            num_attachments=d.get("NumAttachments", 0),
            attachments=d.get("Attachments", []),
            mime_type=d.get("MIMEType", ""),
            headers=d.get("Headers", ""),
            writer_type=d.get("WriterType", 0),
        )


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Reassemble emails from ProtonMail export based on labels.")
    parser.add_argument("input_dir", help="Directory containing the ProtonMail export.")
    parser.add_argument("output_dir", help="Directory to store reassembled emails.")
    parser.add_argument("--folders-config", help="YAML file specifying which folders to create.", default=None)

    args = parser.parse_args()

    config = Config(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        folders_config=args.folders_config
    )

    if not os.path.exists(config.input_dir):
        print(f"Input directory does not exist: {config.input_dir}")
        return

    if not os.path.exists(config.output_dir):
        os.makedirs(config.output_dir)

    labels = LabelDescr.load(config)
    if not labels:
        print("No labels found in the export.")
        return

    folders = Folder.setup(config, labels)
    if not folders:
        print("No folders to create based on the provided configuration.")
        return

    print(f"Creating {len(folders)} folders...")
    for folder in folders:
        folder.create()

    label_map = {folder.label.id: folder for folder in folders}
    for root, _, files in os.walk(config.input_dir):
        for file in files:
            if not file.endswith(".json"):
                continue
            if file == "labels.json":
                continue
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    meta = MessageMeta.from_dict(data["Payload"])
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON file {file_path}: {e}")
                    continue
                except:
                    print(f"Unexpected error processing file {file_path}")
                    continue
            folder = None
            for label_id in meta.label_ids:
                if label_id in label_map:
                    folder = label_map[label_id]
                    break
            if not folder:
                continue

            eml_path = os.path.join(root, f"{meta.id}.eml")
            if not os.path.exists(eml_path):
                print(f"EML file not found for message ID {meta.id}: {eml_path}")
                continue

            dest_path = os.path.join(folder.path, f"{meta.id}.eml")
            try:
                os.link(eml_path, dest_path)
                folder.count += 1
                print(f"Linked message ID {meta.id} to folder '{folder.label.name}'")
            except Exception as e:
                print(f"Failed to link message ID {meta.id} to folder '{folder.label.name}': {e}")




if __name__ == "__main__":
    main()