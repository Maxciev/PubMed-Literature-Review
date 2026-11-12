#!/usr/bin/env python3
"""PubMed access through NCBI E-utilities, used when the PubMed connector is not available.

Standard library only. Output is JSON on stdout, shaped like the connector's results.

  python3 pubmed.py search "scaphoid nonunion[tiab]" --max 20 --sort relevance
  python3 pubmed.py metadata 31226479 30012345 --abstract-chars 1500
  python3 pubmed.py convert 31226479 10.1016/j.jhsa.2019.01.001

Optional environment variables: NCBI_API_KEY (10 requests/s instead of 3), NCBI_EMAIL
(sent to NCBI with every request, as their usage policy asks).
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
IDCONV = "https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/"
TOOL = "pubmed-literature-review-skill"
API_KEY = os.environ.get("NCBI_API_KEY", "")
EMAIL = os.environ.get("NCBI_EMAIL", "")
MIN_INTERVAL = 0.11 if API_KEY else 0.34
SORTS = {"relevance": "relevance", "pub_date": "pub_date", "author": "Author",
         "journal_name": "JournalName", "title": "title"}

_last_call = 0.0


def _get(url, params, retries=4):
    """GET with NCBI's rate limit and retries on 429 / 5xx / network errors."""
    global _last_call
    params = dict(params, tool=TOOL)
    if EMAIL:
        params["email"] = EMAIL
    if API_KEY:
        params["api_key"] = API_KEY
    full = url + "?" + urllib.parse.urlencode(params, doseq=True)
    for attempt in range(retries + 1):
        wait = MIN_INTERVAL - (time.monotonic() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.monotonic()
        try:
            with urllib.request.urlopen(full, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or attempt == retries:
                raise RuntimeError(f"HTTP {e.code}: {e.read()[:300].decode(errors='replace')}")
        except urllib.error.URLError:
            if attempt == retries:
                raise
        time.sleep(2 ** attempt)


def search(query, max_results=20, sort="relevance", date_from=None, date_to=None,
           datetype="pdat", retstart=0):
    params = {"db": "pubmed", "term": query, "retmax": max_results, "retstart": retstart,
              "retmode": "json", "sort": SORTS[sort]}
    if date_from or date_to:
        params.update(datetype=datetype, mindate=date_from or "1800", maxdate=date_to or "3000")
    res = json.loads(_get(EUTILS + "esearch.fcgi", params))["esearchresult"]
    if "ERROR" in res:
        raise RuntimeError(res["ERROR"])
    total = int(res.get("count", 0))
    pmids = res.get("idlist", [])
    return {"pmids": pmids, "total_count": total, "returned_count": len(pmids),
            "query_translation": res.get("querytranslation", ""),
            "has_more": retstart + len(pmids) < total,
            "warnings": res.get("warninglist", {}).get("outputmessages", [])}


def _text(el):
    return "".join(el.itertext()).strip() if el is not None else ""


def _year(article):
    for path in ("MedlineCitation/Article/Journal/JournalIssue/PubDate/Year",
                 "MedlineCitation/Article/ArticleDate/Year"):
        y = article.findtext(path)
        if y:
            return y
    medline = article.findtext("MedlineCitation/Article/Journal/JournalIssue/PubDate/MedlineDate")
    return medline[:4] if medline else ""


def _parse(article, abstract_chars):
    mc = article.find("MedlineCitation")
    art = mc.find("Article")
    ids = {i.get("IdType"): i.text for i in article.findall("PubmedData/ArticleIdList/ArticleId")}
    doi = ids.get("doi") or next((e.text for e in art.findall("ELocationID")
                                  if e.get("EIdType") == "doi"), None)
    parts = []
    for a in art.findall("Abstract/AbstractText"):
        label = a.get("Label")
        parts.append(f"{label}: {_text(a)}" if label else _text(a))
    abstract = " ".join(parts)
    if abstract_chars and len(abstract) > abstract_chars:
        abstract = abstract[:abstract_chars].rstrip() + " [...]"
    authors, affiliations = [], []
    for au in art.findall("AuthorList/Author"):
        name = au.findtext("CollectiveName") or " ".join(
            x for x in (au.findtext("LastName"), au.findtext("Initials")) if x)
        authors.append(name)
        aff = au.findtext("AffiliationInfo/Affiliation")
        if aff and aff not in affiliations:
            affiliations.append(aff)
    issue = art.find("Journal/JournalIssue")
    epub = art.find("ArticleDate")
    return {
        "pmid": mc.findtext("PMID"),
        "title": _text(art.find("ArticleTitle")),
        "abstract": abstract,
        "authors": authors,
        "affiliations": affiliations,
        "journal": art.findtext("Journal/Title"),
        "journal_iso": art.findtext("Journal/ISOAbbreviation"),
        "year": _year(article),
        "epub_date": "-".join(epub.findtext(k) for k in ("Year", "Month", "Day")) if epub is not None else None,
        "volume": issue.findtext("Volume") if issue is not None else None,
        "issue": issue.findtext("Issue") if issue is not None else None,
        "pages": art.findtext("Pagination/MedlinePgn"),
        "doi": doi,
        "pmcid": ids.get("pmc"),
        "publication_types": [_text(p) for p in art.findall("PublicationTypeList/PublicationType")],
        "mesh_terms": [_text(m) for m in mc.findall("MeshHeadingList/MeshHeading/DescriptorName")],
    }


def metadata(pmids, abstract_chars=0, batch=200):
    out = []
    for i in range(0, len(pmids), batch):
        chunk = pmids[i:i + batch]
        root = ET.fromstring(_get(EUTILS + "efetch.fcgi",
                                  {"db": "pubmed", "id": ",".join(chunk), "retmode": "xml"}))
        out += [_parse(a, abstract_chars) for a in root.findall("PubmedArticle")]
    found = {a["pmid"] for a in out}
    return {"articles": out, "not_found": [p for p in pmids if p not in found]}


def convert(ids):
    """PMID / PMCID / DOI conversion. The PMC converter only knows PMC articles and refuses mixed
    identifier types in one call, so ids are grouped by type and a DOI it does not know is looked
    up with an esearch [doi] query."""
    groups = {}
    for i in ids:
        kind = "pmid" if i.isdigit() else "pmcid" if i.upper().startswith("PMC") else "doi"
        groups.setdefault(kind, []).append(i)
    records = []
    for kind, chunk in groups.items():
        res = json.loads(_get(IDCONV, {"ids": ",".join(chunk), "format": "json", "idtype": kind}))
        for r in res.get("records", []):
            rec = {k: r.get(k) for k in ("requested-id", "pmid", "pmcid", "doi", "errmsg")}
            if rec["pmid"] is not None:
                rec["pmid"] = str(rec["pmid"])
            if kind == "doi" and not rec["pmid"]:
                found = search(f'"{rec["requested-id"]}"[doi]', max_results=2)["pmids"]
                if len(found) == 1:
                    rec.update(pmid=found[0], doi=rec["requested-id"], errmsg=None,
                               source="esearch (not in PMC)")
            records.append(rec)
    return {"records": records}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search", help="PubMed search, returns PMIDs")
    s.add_argument("query")
    s.add_argument("--max", type=int, default=20)
    s.add_argument("--sort", choices=sorted(SORTS), default="relevance")
    s.add_argument("--date-from")
    s.add_argument("--date-to")
    s.add_argument("--datetype", choices=["pdat", "edat", "mdat"], default="pdat")
    s.add_argument("--retstart", type=int, default=0)
    m = sub.add_parser("metadata", help="Article metadata for PMIDs")
    m.add_argument("pmids", nargs="+")
    m.add_argument("--abstract-chars", type=int, default=0, help="truncate abstracts (0 = full)")
    c = sub.add_parser("convert", help="PMID / PMCID / DOI conversion")
    c.add_argument("ids", nargs="+")
    a = p.parse_args()
    try:
        if a.cmd == "search":
            out = search(a.query, a.max, a.sort, a.date_from, a.date_to, a.datetype, a.retstart)
        elif a.cmd == "metadata":
            out = metadata([x.strip(",") for x in a.pmids], a.abstract_chars)
        else:
            out = convert(a.ids)
    except (urllib.error.URLError, RuntimeError, ET.ParseError) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == "__main__":
    main()
