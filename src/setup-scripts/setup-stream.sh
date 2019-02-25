#! /usr/bin/env bash

streamName=""
streamShards=""
accountID=""

# Enter Kinesis stream name
while [[ -z "$streamName" ]]
do
  read -p "Enter kinesis stream name: " streamName
done


# Enter number of shards
while [[ -z "$streamShards" ]]
do
  read -p "Enter the number of shards(*note: Read https://docs.aws.amazon.com/streams/latest/dev/amazon-kinesis-streams.html#how-do-i-size-a-stream for determining the number of shards ): " streamShards
done

# get account ID
accountID=$(aws sts get-caller-identity --output text --query 'Account')
if [ -z "$accountID" ]
  then
    echo "Set up your AWS ACCESS KEY, SECRET and REGION in bash_profile as environment variables"
    exit 1;
fi

# Create kinesis stream
aws kinesis create-stream --stream-name $streamName --shard-count $streamShards
