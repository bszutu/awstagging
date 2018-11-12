## Python script to tag EBS with all the tags from the instance and Snapshots with tags from AMI

Repo created by Ben Szutu <ben.szutu@autodesk.com>
Credit for the script is within the script comment

This repository contains the source code for the awstagging

## Files

The following files are located in this repo:
* tagging.py - the python script that can be ran from command line to tag the EBS and the Snapshot
* README.md - this file

## How does it work
The tagging function will search all of your EBS and tag them with tags the parent instances and
it will search all of your snapshot and tag them with tags from the parent AMI

For any resource (EBS or Snapshot) that does not have a parent.  EBS not associated with an instance 
or snapshot that has it's parent AMI deregistered, it will mark it as "UNUSED" so it can be cleaned up

## To use as a lambda function
this function can be easily adapted to lambda by adding in the missing lambda define
