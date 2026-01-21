import time

from click import unstyle

from ai.backend.client.cli.pretty import PrintStatus, bold, inverse, italic, print_pretty, underline


def test_pretty_output():
    # Currently this is a graphical test -- you should show the output
    # using "-s" option in pytest and check it manually with your eyes.

    pprint = print_pretty

    print("normal print")
    pprint("wow " + bold("wow") + " wow!")
    print("just " + underline("print") + " " + italic("grrrrrgh") + "... wooah!")
    pprint(inverse("wow") + "!!", status=PrintStatus.WARNING)
    pprint("some long loading.... zzzzzzzzzzzzz", status=PrintStatus.WAITING)
    time.sleep(0.3)
    pprint("doing something...", status=PrintStatus.WAITING)
    time.sleep(0.3)
    pprint("done!", status=PrintStatus.DONE)
    pprint("doing " + bold("something") + "...", status=PrintStatus.WAITING)
    time.sleep(0.5)
    pprint("doing more...", status=PrintStatus.WAITING)
    time.sleep(0.3)
    pprint("failed!", status=PrintStatus.FAILED)
    print("normal print")


def test_unstyle():
    print(unstyle(underline("non-underline")))
    print(unstyle(italic("non-italic")))


if __name__ == "__main__":
    test_pretty_output()
