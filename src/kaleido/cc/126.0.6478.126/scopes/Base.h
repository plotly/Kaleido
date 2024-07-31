// Build call arguments is fucked
//
// Created by jmmease on 6/17/20.
//

#ifndef CHROMIUM_BASESCOPE_H
#define CHROMIUM_BASESCOPE_H
#include "base/strings/string_util.h"
#include "base/command_line.h"

#include <list>
#include <vector>
#include <string>


namespace kaleido {
    namespace scopes {
        class BaseScope {
            public:
                BaseScope();
                BaseScope(const BaseScope &v);
                virtual ~BaseScope();

                virtual std::string ScopeName() = 0;
                virtual base::Value::List BuildCallArguments();
				// For above, theoretically a JSON list would be 
				// fine and we should give them 
				// that option.
                std::list<std::string> ScriptTags();
                std::list<std::string> LocalScriptFiles();
                std::string GetCommandLineSwitch(std::string name);
                bool HasCommandLineSwitch(std::string name);

                std::string errorMessage;

            public:
                std::list<std::string> scriptTags;
                std::list<std::string> localScriptFiles;
                const base::raw_ptr<BaseScope> plugin;
        };

        BaseScope::BaseScope(): errorMessage(), scriptTags(), localScriptFiles() {}
        BaseScope::BaseScope(const BaseScope &v):
            scriptTags(v.scriptTags),
            localScriptFiles(v.localScriptFiles)
            {}

        BaseScope::~BaseScope() {
            delete plugin;
        }

        base::Value::List BaseScope::BuildCallArguments() {
			base::Value::List empty;
            return empty;
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
