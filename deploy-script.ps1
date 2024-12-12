gcloud functions deploy line-bot `
--env-vars-file .env.yaml `
--gen2 `
--region=asia-east1 `
--runtime=python311 `
--source=./deploy `
--entry-point=hello_bot `
--trigger-http `
--allow-unauthenticated
