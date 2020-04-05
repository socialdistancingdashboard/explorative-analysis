import matplotlib.pyplot as plt
import seaborn as sns
import requests
import pandas as pd
import numpy as np

def load_topojson():
    url_topojson = 'https://images.everyonecounts.de/germany.json'
    r = requests.get(url_topojson)
    jsondump = r.json()
    county_names = []
    county_ids = []
    for county in jsondump["objects"]["counties"]["geometries"]:
        county_names.append(county["properties"]["name"] + " (" + county["properties"]["districtType"]+")")
        county_ids.append(county["id"])
    state_names = []
    state_ids = []
    for state in jsondump["objects"]["states"]["geometries"]:
        state_names.append(state["properties"]["name"])
        state_ids.append(state["id"])
    return county_names, county_ids, state_names, state_ids

def load_real_data():
    response = requests.get('https://im6qye3mc3.execute-api.eu-central-1.amazonaws.com/prod')
    jsondump = response.json()["body"]
    county_names, county_ids, state_names, state_ids = load_topojson()
    id_to_name = {cid: county_names[idx] for idx, cid in enumerate(county_ids)}

    # get names for all scores
    scorenames = []
    for (date, row) in list(jsondump.items()):
        for cid, scores in row.items():
            for key in scores.keys():
                if key not in scorenames:
                    scorenames.append(key)
    scorenames = [key for key in scorenames if '_score' in key]

    # prepare lists
    scorevalues = {scorename: [] for scorename in scorenames}
    ids = []
    names = []
    dates = []

    # loop over data
    for (date, row) in list(jsondump.items()):
        for cid, scores in row.items():
            ids.append(cid)
            names.append(id_to_name[cid])
            dates.append(date)
            for scorename in scorenames:
                if scorename in scores:
                    scorevalue = scores[scorename] * 100
                else:
                    scorevalue = None
                scorevalues[scorename].append(scorevalue)

    # create dataframe
    df_scores = pd.DataFrame({
        "id": ids,
        "name": names,
        "date": dates
    })

    # add scores
    for scorename in scorenames:
        df_scores[scorename] = scorevalues[scorename]
    df_scores = df_scores.replace([np.inf, -np.inf], np.nan)

    return df_scores, scorenames

if __name__ == "__main__":
    df_scores = load_real_data()
    for score in list(df_scores.columns[3:]):
        gb_object = df_scores.groupby("date", as_index=False)[score].max()
        gb_object = gb_object.loc[gb_object["date"] > "2020-03-20"]
        plt.figure()
        sns.lineplot(gb_object["date"], gb_object[score])
        plt.xticks(rotation=90)
        y_min, y_max = plt.ylim()
        plt.ylim(0, y_max)
        plt.tight_layout()
        plt.savefig(f"plots/{score}_MAX.png")

    for date, counter in zip(df_scores["date"], range(150)):
        gb_object = df_scores.groupby([date], as_index=False)["gmap_score"].rolling(3).mean()
        sns.lineplot(gb_object["date"], gb_object["gmap_score"])
        plt.xticks(rotation=90)

