# GitHub CLI api
# https://cli.github.com/manual/gh_api

repos=(
    zepben/web-client-ci-test
    zepben/python-lib-ci-test
    zepben/npm-lib-ci-test
    zepben/load-schema-migrator
    zepben/temporal-platform-definitions
    zepben/temporal-platform-worker
)

for repo in ${repos[@]}; do
    echo "Fixing repo permissions: $repo"
    gh api \
      --method POST \
      -H "Accept: application/vnd.github+json" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      /repos/$repo/rulesets \
      --input branch-protection-rules.json
done

# The following section is an example of updating existing rulesets
# for repo in ${repos[@]}; do
#     echo "Fixing repo permissions for $repo: "
#     id=$(gh api \
#       -H "Accept: application/vnd.github+json" \
#       -H "X-GitHub-Api-Version: 2022-11-28" \
#       /repos/$repo/rulesets  | jq '.[].id')
#     gh api \
#       -H "Accept: application/vnd.github+json" \
#       -H "X-GitHub-Api-Version: 2022-11-28" \
#       /repos/$repo/rulesets/${id} \
#       --method PUT \
#       --input branch-protection-rules.json
# done
