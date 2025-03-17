# GitHub CLI api
# https://cli.github.com/manual/gh_api

repos=(
    zepben/zepben.github.io
    zepben/docusaurus-preset
    zepben/network-diagnostic-tool
    zepben/evolve
    zepben/bitbucket-trigger-pipeline-action
    zepben/cimdemo
    zepben/evolve-python-sdk-tests
    zepben/docusaurus-action
    zepben/docusaurus-components
    zepben/clickup-automation
    zepben/2030-5-model-site
    zepben/psse-translator
    zepben/repo-template-css
    zepben/sincal-to-evolve
    zepben/load-synthesiser
    zepben/evolve-azure-templates
    zepben/python-sdk-demos
    zepben/jvm-sdk-demos
    zepben/kotlin-oauth2-server
    zepben/tas-geojson-transformer
    zepben/zepben-auth-python
    zepben/fault-location
    zepben/osi-pi-agent
    zepben/python-sdk-examples
    zepben/bb_model_comparator
    zepben/network-explorer
    zepben/ewb-sandbox-demo
    zepben/zepben-ca
    zepben/hosting_capacity_analysis
    zepben/ee-evolve-deployment
    zepben/evolve-functional-testing
    zepben/evolve-tutorials
    zepben/wp-network-extractor
    zepben/fault-location-trial
    zepben/datamodel-documentation
    zepben/synthetic-loads
    zepben/opendss-ingestor
    zepben/ewb-data-model-requirements
    zepben/opendss-exporter
    zepben/ee_hybrid_premise_ingestor
    zepben/cim-to-opendss-processor
    zepben/load-aggregator
    zepben/how-tos
    zepben/ea-extractor
    zepben/lasarus-nr-client
    zepben/zepben-auth-jvm
    zepben/sincal-load-allocation
    zepben/ednar-reporting-service
    zepben/network-trace-extractor
    zepben/opendss-scheduler
    zepben/hosting-capacity-study
    zepben/sincal-exporter
    zepben/go-scheduler
    zepben/csharp-extensions
    zepben/sincal-model-generator
    zepben/ausnet-daily-script
    zepben/sincal-automation-ee
    zepben/hosting-capacity-intervention-analysis
    zepben/intellij-idea-settings
    zepben/interval-data-loader
    zepben/sincal-model-refiner
    zepben/ednar-app-server
    zepben/ms-fault-location
    zepben/ednar-customer-scripts
    zepben/hv-network-tracing
    zepben/edith-sdk
    zepben/lasarus-nrbu-archive-read-only
    zepben/lasarus-server
    zepben/lasarus-linux-agent
    zepben/lasarus-ar-client
    zepben/conductor-code-transfer
    zepben/lasarus-documentation
    zepben/smart-load-plugin-setup
    zepben/evolve-datamodel-site
    zepben/ewb-load-ui
    zepben/customer-info
    zepben/questdb
    zepben/surf
    zepben/powerfactory-template-service
    zepben/hosting-capacity-runner
    zepben/hosting-capacity-example
    zepben/pcor-pqv-processor
    zepben/ednar-cppal-usb-polling-service
    zepben/noose
    zepben/pof-historian-service
    zepben/company-website
    zepben/eslint-config-ts
    zepben/ednar-dms-agent
    zepben/feeder-load-aggregator
    zepben/artificial-load-profiles-generator
    zepben/spatialeye-extractor
    zepben/ldap-user-polling-service
    zepben/aft-account-customizations
    zepben/aft-account-provisioning-customizations
    zepben/aft-global-customizations
    zepben/opendss-debugger
    zepben/load-clustering
    zepben/zconf
    zepben/maven-login
    zepben/cgmes-importer
    zepben/opendss-jvm-executor
    zepben/load-process-cs
    zepben/ops-lambdas
    zepben/powercor-ednar-config
    zepben/load-data-ingestor
    zepben/platform-workflows
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
