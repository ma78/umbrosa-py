#!/usr/bin/env python3
import os

from aws_cdk import App

from cdk.cdk_stack import UmbrosaBackendStack


app = App()
UmbrosaBackendStack(app, "UmbrosaBackend")

app.synth()
