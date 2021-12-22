import sys


from graphviz import Digraph
from joblib import Parallel, delayed
from pprint import pprint
import pandas as pd


import json

j = json.load(open("data.json"))

skills = j["skills"]
skills.update(j["knowledge"])

occupations = {}
for skill in skills.values():
    for occupation in skill["occupations"]:
        if occupation["relation_type"] != "essential":
            continue
        if occupation["value"] not in occupations:
            existing_occupation = {"value": occupation["value"], "skills": set()}
            occupations[occupation["value"]] = existing_occupation
        else:
            existing_occupation = occupations[occupation["value"]]
        existing_occupation["skills"].add(skill["value"])


def safe(t):
    return t.replace("/", "-").replace(" ", "_")


def md(t):
    return safe(t) + ".md"


def full_link(t):
    return (
        "https://github.com/asomas/skills_analysis/blob/master/occupations/"
        + safe(t)
        + ".md"
    )


def link(t, prefix=""):
    return f"[{t}]({prefix + md(t)})"


def make_occupation_page(search, file):
    occupation = occupations[search]
    print(f"# Occupation {occupation['value']}", file=file)

    max_count = len(occupation["skills"])
    print(f"## Number skills {max_count}", file=file)
    print("### Similar occupations:", file=file)
    values = []
    for o in occupations.values():
        if o["value"] == search:
            continue
        match_count = len(o["skills"].intersection(occupation["skills"]))
        difference = len(o["skills"].difference(occupation["skills"]))
        number_skills = len(o["skills"])
        values.append(
            {
                "occupation": link(o["value"]),
                "skills in this occupation": number_skills,
                f"skills that match {search}": match_count,
                f"percentage match with {search}": match_count / max_count,
                f"skills not in {search}": difference,
            }
        )

    df = pd.DataFrame(values)
    df.sort_values(by=f"skills that match {search}", ascending=False, inplace=True)
    df = df[df[f"percentage match with {search}"] > 0.1]
    print(df.to_markdown(index=False), file=file)

    gra = Digraph(format="cmapx")
    gra.graph_attr["rankdir"] = "db"
    gra.node("center", search)
    for (i, (_, row)) in enumerate(df.head(5).iterrows()):
        percent_match = row[f"percentage match with {search}"]
        o = row["occupation"]
        a, b = o.find("["), o.find("]")
        o = o[a:b]
        gra.node(f"n{i}", f"{o} ({max_count} skills)", url=full_link(o))
        gra.edge(
            "center",
            f"n{i}",
            label="{:.0}%".format(percent_match),
            weight=str(percent_match),
        )
        gra.render("occupations/" + safe(search) + "")
    sys.exit(0)


def process(o):
    with open(f"occupations/{safe(o)}.md", "w") as file:
        print("writing ", o)
        make_occupation_page(o, file)


def index(file):
    values = []
    for o in occupations.values():
        values.append(
            {
                "occupation": link(o["value"], prefix="occupations/"),
                "skills": len(o["skills"]),
            }
        )
    df = pd.DataFrame(values)
    df.sort_values(by="occupation", inplace=True)
    print("# Occupations:", file=file)
    print(df.to_markdown(index=False), file=file)


with open("readme.md", "w") as file:
    index(file)
# Parallel(n_jobs=1)(delayed(process)(o) for o in occupations.keys())
process("nanny")
