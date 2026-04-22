import requests
import pandas as pd
import json

url = 'http://localhost:8080'

def ruleEvaluateByGroup(evalName, groupID, ruleGroupID, labelingMethod="sign"):
    """
    API Request to Knox to run Rule Evaluation Algorithm.

    Returns:
    metrics (list of pandas DataFrames): purity_metrics, designToRule
    """
    response = requests.post(
        url + '/rule/evaluate?' +
        "evaluationName=" + evalName + '&' +
        "designGroupID=" + groupID + '&' +
        "rulesGroupID=" + ruleGroupID + '&' +
        "labelingMethod=" + labelingMethod
    )

    print("Status code:", response.status_code)
    print("Response text:", response.text)

    return processRuleEval(response)


def ruleEvaluateByDesigns(evalName, designIDs, ruleGroupID, designScores, labelingMethod="sign"):
    designSpaceIDs = listToStringList(designIDs)
    designScoresStr = listToStringList(designScores)

    response = requests.post(
        url + '/rule/evaluate?' +
        "evaluationName=" + evalName + '&' +
        "designSpaceIDs=" + designSpaceIDs + '&' +
        "rulesGroupID=" + ruleGroupID + '&' +
        "designScores=" + designScoresStr + '&' +
        "labelingMethod=" + labelingMethod
    )

    return processRuleEval(response)


def getRuleEvaluation(evalName):
    response = requests.get(url + '/rule/getEvaluation?' + "evaluationName=" + evalName)
    return processRuleEval(response)


def deleteRuleEvaluation(evalName):
    response = requests.delete(url + '/rule?' + "evaluationName=" + evalName)

    if not response.text:
        return f'"{evalName}" Successfully Deleted'
    else:
        return response.text


def processRuleEval(response):
    json_data = json.loads(response.text)

    print("Parsed JSON response:")
    print(json_data)

    if "evaluationResults" not in json_data:
        print("Missing 'evaluationResults' in response.")
        return json_data

    if "designToRule" not in json_data:
        print("Missing 'designToRule' in response.")
        return json_data

    purity_metrics_df = pd.DataFrame(json_data["evaluationResults"]).T
    print("purity_metrics_df columns:", purity_metrics_df.columns.tolist())

    designToRule_df = pd.DataFrame(
        json_data["designToRule"],
        index=json_data["designToRule"]["designIDs"]
    )
    cols = designToRule_df.columns.to_list()
    cols.remove("labels")
    cols.remove("scores")
    cols.remove("designIDs")
    cols = ["labels", "scores"] + cols
    designToRule_df = designToRule_df[cols]

    if "scores" in designToRule_df.columns:
        designToRule_df = designToRule_df.sort_values("scores")

    return purity_metrics_df, designToRule_df


def listToStringList(list_input):
    return ",".join(list_input)

## test functions
if __name__ == "__main__":
    print("Test 1: ruleEvaluateByGroup")

    evalName = "test_eval_1"
    groupID = "ui_design"
    ruleGroupID = "rule_group_A"

    try:
        metrics, df = ruleEvaluateByGroup(
            evalName,
            groupID,
            ruleGroupID,
            labelingMethod="sign"
        )

        print("\nPurity Metrics:")
        print(metrics.head())

        print("\nDesignToRule:")
        print(df.head())

    except Exception as e:
        print("ERROR:", e)