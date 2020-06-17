//
// Created by jmmease on 6/17/20.
//

#include "headless/public/devtools/domains/runtime.h"

#include <list>
#include <vector>
#include <string>

#ifndef CHROMIUM_BASEPLUGIN_H
#define CHROMIUM_BASEPLUGIN_H


class BasePlugin {
public:
    BasePlugin();
    BasePlugin(const BasePlugin &v);
    virtual ~BasePlugin();

    virtual std::vector<std::unique_ptr<::headless::runtime::CallArgument>> BuildCallArguments();
    std::list<std::string> ScriptTags();
    std::list<std::string> LocalScriptFiles();

protected:
    std::list<std::string> scriptTags;
    std::list<std::string> localScriptFiles;
    const BasePlugin *plugin;
};

BasePlugin::BasePlugin(): scriptTags(), localScriptFiles() {}
BasePlugin::BasePlugin(const BasePlugin &v):
    scriptTags(v.scriptTags),
    localScriptFiles(v.localScriptFiles)
    {}

BasePlugin::~BasePlugin() {
    delete plugin;
}

std::vector<std::unique_ptr<::headless::runtime::CallArgument>> BasePlugin::BuildCallArguments() {
    return std::vector<std::unique_ptr<::headless::runtime::CallArgument>>();
}

std::list<std::string> BasePlugin::ScriptTags() {
    // Return vector as value so that it is copied and caller is free to mutate it
    return scriptTags;
}

std::list<std::string> BasePlugin::LocalScriptFiles() {
    // Return vector as value so that it is copied and caller is free to mutate it
    return localScriptFiles;
}


#endif //CHROMIUM_BASEPLUGIN_H
