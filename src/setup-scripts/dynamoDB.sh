#! /usr/bin/env bash

# Create kinesis stream
aws dynamodb create-table --table-name Baseline_Schemas \
--attribute-definitions AttributeName=Property,AttributeType=S AttributeName=Schema,AttributeType=S \
--key-schema AttributeName=Property,KeyType=HASH AttributeName=Schema,KeyType=RANGE \
--provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
