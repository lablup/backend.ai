import sys

pr_number = sys.argv[1]
pr_title_feat = sys.argv[2]
pr_title_cont = sys.argv[3 : len(sys.argv)]

index = pr_title_feat.find(":")

new_title = pr_number + "." + pr_title_feat[0:index] + ".md"
file = open(new_title, "w")

file.write(" ".join(pr_title_cont))
file.close()
