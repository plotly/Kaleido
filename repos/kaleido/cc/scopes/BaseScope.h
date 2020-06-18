//
// Created by jmmease on 6/17/20.
//

#include "headless/public/devtools/domains/runtime.h"

#include <list>
#include <vector>
#include <string>

#ifndef CHROMIUM_BASEPLUGIN_H
#define CHROMIUM_BASEPLUGIN_H


class BaseScope {
public:
    BaseScope();
    BaseScope(const BaseScope &v);
    virtual ~BaseScope();

    virtual std::string PluginName() = 0;
    virtual std::vector<std::unique_ptr<::headless::runtime::CallArgument>> BuildCallArguments();
    std::list<std::string> ScriptTags();
    std::list<std::string> LocalScriptFiles();

protected:
    std::list<std::string> scriptTags;
    std::list<std::string> localScriptFiles;
    const BaseScope *plugin;
};

BaseScope::BaseScope(): scriptTags(), localScriptFiles() {}
BaseScope::BaseScope(const BaseScope &v):
    scriptTags(v.scriptTags),
    localScriptFiles(v.localScriptFiles)
    {}

BaseScope::~BaseScope() {
    delete plugin;
}

std::vector<std::unique_ptr<::headless::runtime::CallArgument>> BaseScope::BuildCallArguments() {
    return std::vector<std::unique_ptr<::headless::runtime::CallArgument>>();
}

std::list<std::string> BaseScope::ScriptTags() {
    // Return vector as value so that it is copied and caller is free to mutate it
    return scriptTags;
}

std::list<std::string> BaseScope::LocalScriptFiles() {
    // Return vector as value so that it is copied and caller is free to mutate it
    return localScriptFiles;
}


#endif //CHROMIUM_BASEPLUGIN_H
