#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import json
from common import *
from xbmcswift2 import Module


history_list = Module(__name__)


@history_list.route("/add/<plugin_url>/<name>", options={"name": "test"})
def add_history(plugin_url, name):
    plugin = history_list.plugin
    history = plugin.get_storage("history")
    if "list" not in history:
        history["list"] = []
    history["list"].append({"url": plugin_url,
                            "name": name})


@history_list.route("/list")
def list_history():
    plugin = history_list.plugin
    history = plugin.get_storage("history")
    if "list" in history:
        for item in history["list"]:
            yield {
                'label': item["name"],
                'path': item["url"],
                'is_playable': True
            }
