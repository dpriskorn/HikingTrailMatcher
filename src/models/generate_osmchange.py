import logging
import os
import xml.etree.ElementTree as ET
from datetime import date
from typing import Any

from OSMPythonTools.api import Api
from wikibaseintegrator.wbi_helpers import execute_sparql_query

import config
from src.console import console
from src.models.project_base_model import ProjectBaseModel

logger = logging.getLogger(__name__)


class OSMRelation:
    def __init__(self, osm_id: int, version: int, tags: dict[str, str]):
        self.id = osm_id
        self.version = version
        self.tags = tags


class OsmChangeGenerator(ProjectBaseModel):
    rdf_entity_prefix = "http://www.wikidata.org/entity/"
    api = Api()
    output_path: str = ""
    mismatch_report_path: str = ""
    modify_blocks: list = []
    mismatches: list[tuple[int, str, str]] = []
    mismatch_count: int = 0
    examined_count: int = 0
    already_tagged_count: int = 0
    patched_count: int = 0

    class Config:
        arbitrary_types_allowed = True

    def generate(self) -> dict[str, int]:
        self.setup_wbi()
        items = self.__get_items_with_osm_id__()
        today = date.today().isoformat()
        self.output_path = f"output/osmchange-{today}.osc"
        self.mismatch_report_path = f"output/osmchange-{today}-mismatches.csv"
        os.makedirs("output", exist_ok=True)
        console.print(
            f"Generating osmChange for {len(items)} Swedish hiking trails "
            f"with P402 set"
        )
        for item in items:
            wd_qid = item["item"]["value"].replace(self.rdf_entity_prefix, "")
            osm_id = int(item["osm"]["value"])
            self.__process_relation__(wd_qid, osm_id)
        self.__write_mismatch_report__()
        self.__write_osmchange__()
        summary = {
            "examined": self.examined_count,
            "already_tagged": self.already_tagged_count,
            "patched": self.patched_count,
            "mismatched": self.mismatch_count,
        }
        console.print(
            f"Done. Examined: {summary['examined']}, "
            f"already tagged: {summary['already_tagged']}, "
            f"patched: {summary['patched']}, "
            f"mismatches: {summary['mismatched']}"
        )
        return summary

    def __get_items_with_osm_id__(self) -> list[dict[str, Any]]:
        result = execute_sparql_query(
            f"""
            SELECT distinct ?item ?osm ?lastUpdate WHERE {{
              ?item wdt:P31/wdt:P279* wd:Q2143825;
                    wdt:P17 wd:{config.country_qid};
                    wdt:P402 ?osm.
              MINUS {{ ?item wdt:P31 wd:Q116787033 }}
              OPTIONAL {{
                ?item p:P9660 ?statement.
                ?statement ps:P9660 wd:Q936.
                ?statement pq:P5017 ?lastUpdate.
              }}
            }}
            """
        )
        return result["results"]["bindings"]

    def __fetch_osm_relation__(self, osm_id: int) -> OSMRelation | None:
        try:
            relation = self.api.query(f"relation/{osm_id}")
            if not relation.isValid():
                logger.warning(f"Relation {osm_id} not found in OSM")
                return None
            tags = relation.tags()
            version = relation.version()
            return OSMRelation(osm_id=osm_id, version=int(version), tags=tags)
        except Exception as e:
            logger.error(f"Failed to fetch relation {osm_id}: {e}")
            return None

    def __process_relation__(self, wd_qid: str, osm_id: int) -> None:
        self.examined_count += 1
        console.print(f"Processing relation {osm_id} (Q{wd_qid})")
        relation = self.__fetch_osm_relation__(osm_id)
        if not relation:
            return
        self.__classify__(wd_qid, relation)

    def __classify__(self, wd_qid: str, relation: OSMRelation) -> str:
        existing = relation.tags.get("wikidata", "")
        if existing == wd_qid:
            logger.info(f"Relation {relation.id} already has wikidata={wd_qid}")
            self.already_tagged_count += 1
            return "skip"
        elif existing == "":
            logger.info(f"Relation {relation.id} missing wikidata tag, will patch")
            self.__build_modify_block__(relation, wd_qid)
            self.patched_count += 1
            return "patch"
        else:
            logger.warning(f"Relation {relation.id} wikidata={existing} "
                           f"!= Q{wd_qid}, logging mismatch")
            self.__append_mismatch__(relation.id, wd_qid, existing)
            self.mismatch_count += 1
            return "mismatch"

    def __build_modify_block__(self, relation: OSMRelation, wd_qid: str) -> None:
        ET.register_namespace("", "http://openstreetmap.org/org/osmchange")
        modify = ET.Element("modify")
        elem = ET.SubElement(
            modify, "relation",
            id=str(relation.id),
            version=str(relation.version),
        )
        for k, v in relation.tags.items():
            ET.SubElement(elem, "tag", k=k, v=v)
        ET.SubElement(elem, "tag", k="wikidata", v=wd_qid)
        self.modify_blocks.append(modify)

    def __append_mismatch__(self, osm_id: int, wd_qid: str, osm_wikidata: str) -> None:
        self.mismatches.append((osm_id, wd_qid, osm_wikidata))

    def __write_mismatch_report__(self) -> None:
        if not self.mismatches:
            return
        with open(self.mismatch_report_path, "w", encoding="utf-8") as f:
            f.write("osm_id,wd_qid,osm_wikidata\n")
            for osm_id, wd_qid, osm_wikidata in self.mismatches:
                f.write(f"{osm_id},{wd_qid},{osm_wikidata}\n")
        console.print(f"Mismatch report written to {self.mismatch_report_path}")

    def __write_osmchange__(self) -> None:
        if not self.modify_blocks:
            console.print("No patches to write")
            return
        root = ET.Element("osmChange", version="0.6", generator="hiking_trail_matcher")
        for block in self.modify_blocks:
            root.append(block)
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(self.output_path, encoding="UTF-8", xml_declaration=True)
        console.print(f"osmChange written to {self.output_path}")
