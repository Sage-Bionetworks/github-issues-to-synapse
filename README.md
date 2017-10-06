# AWS Lambda - Github issues to Synapse
Write open Github issues to a Synapse table using AWS Lambda.

## Usage

1. Clone this repository.
2. Create a Python virtual environment `virtualenv`.
3. Install dependencies (`pip install -r requirements.txt`).
4. From the repository directory, use the following to create the Lambda code as a `.zip` file:

```
export REPODIR=`pwd`
pushd ${VIRTUAL_ENV}/lib/python2.7/site-packages/
zip ${REPODIR}/lambda-code.zip `find .`
popd
zip -r ${REPODIR}/lambda-code.zip ${REPODIR}/export_repo_issues_to_synapse.py
```

5. Upload to an Amazon S3 bucket:

```
aws s3 cp lambda-code.zip s3://my-bucket-for-lambda
```

6. Create a Lambda function (best practice is to use an IAM role specifically for this task):

```
aws lambda create-function --region us-east-1 --function-name IssuesToSynapse --code S3Bucket=my-bucket-for-lambda,S3Key=lambda-code.zip,S3ObjectVersion=1 --role arn:aws:iam::510534517075:role/MyLambdaRole --handler export_repo_issues_to_synapse.issues_to_table_handler --runtime python2.7 --timeout 100 --memory-size 512
```

## Updating the function

Modifications to the code require re-creating the zip file, uploading to the S3 bucket, and then updating the Lambda function:


```
aws lambda update-function-code --function-name IssuesToSynapse --s3-bucket my-bucket-for-lambda --s3-key export_repo_issues_to_synapse.zip
```
