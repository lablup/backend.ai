import argparse
import json
import sys

import huggingface_hub
import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--author", type=str)
    parser.add_argument("--model", type=str)
    parser.add_argument("--token", type=str)
    return parser.parse_args()


def main(args: argparse.Namespace) -> None:
    try:
        model_card = huggingface_hub.ModelCard.load(
            f"{args.author}/{args.model}",  # e.g. "meta-llama/Meta-LLama-3.1-8B-Instruct",
            token=args.token,  # "hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        )
        for row in model_card.text.strip().split("\n"):
            if row and not row.startswith("#"):
                description = row
                break
        else:
            description = ""
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(1)

    card_data = yaml.load(model_card.content.split("---")[1].strip(), Loader=yaml.SafeLoader)

    output = json.dumps({
        "model_card": model_card.text,
        "description": description,
        "license": card_data.get("license"),
        "pipeline_tag": card_data.get("pipeline_tag"),  # e.g. text-generation
        "tags": card_data.get("tags", []),
    })

    sys.stdout.write(output)


if __name__ == "__main__":
    args = parse_args()
    main(args)
