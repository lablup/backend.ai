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
        description = ""
        for row in model_card.text.strip().split("\n"):
            if row and not row.startswith("#"):
                description = row
                break
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(1)
    card_data = yaml.load(model_card.content.split("---")[1].strip(), Loader=yaml.SafeLoader)
    output = json.dumps({
        "model_card": model_card.text,
        "description": description,
        "license": card_data["license"],  # license
        "pipeline_tag": card_data["pipeline_tag"],  # category
        "tags": card_data["tags"],  # label
    })
    print(output)


if __name__ == "__main__":
    args = parse_args()
    main(args)
