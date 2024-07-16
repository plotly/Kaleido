//
// Created by jmmease on 6/17/20.
//

#include "headless/public/devtools/domains/runtime.h"
#include "base/strings/string_util.h"

#include <list>
#include <vector>
#include <string>

#ifndef CHROMIUM_BASESCOPE_H
#define CHROMIUM_BASESCOPE_H

namespace kaleido {
    namespace scopes {
        class BaseScope {
            public:
                BaseScope();
                BaseScope(const BaseScope &v);
                virtual ~BaseScope();

                virtual std::string ScopeName() = 0;
                virtual std::vector<std::unique_ptr<::headless::runtime::CallArgument>> BuildCallArguments();
                std::list<std::string> ScriptTags();
                std::list<std::string> LocalScriptFiles();
                std::string GetCommandLineSwitch(std::string name);
                bool HasCommandLineSwitch(std::string name);

                std::string errorMessage;

            public:
                std::list<std::string> scriptTags;
                std::list<std::string> localScriptFiles;
                const BaseScope *plugin;
        };

        BaseScope::BaseScope(): errorMessage(), scriptTags(), localScriptFiles() {}
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

        bool BaseScope::HasCommandLineSwitch(std::string name) {
            base::CommandLine *commandLine = base::CommandLine::ForCurrentProcess();
            return commandLine->HasSwitch(name);
        }

        std::string BaseScope::GetCommandLineSwitch(std::string name) {
            base::CommandLine *commandLine = base::CommandLine::ForCurrentProcess();
            std::string value = commandLine->GetSwitchValueASCII(name);

            // Trim single and double quotes
            base::TrimString(value, "\"", &value);
            base::TrimString(value, "\'", &value);

            return value;
        }
    }
}

#endif //CHROMIUM_BASESCOPE_H
