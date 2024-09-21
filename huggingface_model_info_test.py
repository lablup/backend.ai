import argparse
import json
import sys

import huggingface_hub
import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--author", type=str)
    parser.add_argument("--model", type=str)
    return parser.parse_args()


def main(args) -> None:
    try:
        model_card = huggingface_hub.ModelCard.load(
            f"{args.author}/{args.model}",  # "meta-llama/Llama-2-13b-chat-hf",
            token="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",
        )
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(1)
    # print(card)
    # print(model_card.text)
    card_data = yaml.load(model_card.content.split("---")[1].strip(), Loader=yaml.SafeLoader)
    # import pprint
    # pprint.pprint(card_data)
    # print(card_data["pipeline_tag"])
    print(json.dumps({"model_card": model_card.text, "pipeline_tag": card_data["pipeline_tag"]}))
    # print(type(model_card.text))


if __name__ == "__main__":
    args = parse_args()
    main(args)
