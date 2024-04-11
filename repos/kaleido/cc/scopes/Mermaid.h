//
// Created by coma007 on 4/4/24.
//
#include "Base.h"
#include "base/bind.h"
#include "base/command_line.h"
#include "base/strings/string_util.h"
#include "base/strings/stringprintf.h"
#include "headless/public/devtools/domains/runtime.h"
#include "../utils.h"
#include <streambuf>
#include <string>
#include <sstream>
#include <iostream>
#include <fstream>

#ifndef CHROMIUM_MERMAIDSCOPE_H
#define CHROMIUM_MERMAIDSCOPE_H

namespace kaleido {
    namespace scopes {

        class MermaidScope : public BaseScope {
        public:
            MermaidScope();

            ~MermaidScope() override;

            MermaidScope(const MermaidScope &v);

            std::string ScopeName() override;

            std::vector<std::unique_ptr<::headless::runtime::CallArgument>> BuildCallArguments() override;
        };

        MermaidScope::MermaidScope() {

            // Initialize mermaid object code
            std::string mermaidInit = "; window.mermaid = mermaid;";

            // Process mermaidjs
            if (HasCommandLineSwitch("mermaidjs")) {
                std::string mermaidjsArg = GetCommandLineSwitch("mermaidjs");

                // Check if value is a URL
                GURL mermaidjsUrl(mermaidjsArg);
                if (mermaidjsUrl.is_valid()) {
                    // ESM module
                    if (kaleido::utils::isESModule(mermaidjsArg)) {
                        scriptTags.push_back("import mermaid from '" + mermaidjsArg + "'" + mermaidInit);
                    }
                    // Default module
                    else {
                        scriptTags.push_back(mermaidjsArg + mermaidInit);
                    }
                } else {
                    // Check if this is a local file path
                    if (std::ifstream(mermaidjsArg)) {
                        localScriptFiles.emplace_back(mermaidjsArg);
                    } else {
                        errorMessage = base::StringPrintf("--mermaidjs argument is not a valid URL or file path: %s",
                                                          mermaidjsArg.c_str());
                        return;
                    }
                }
            } else {
                scriptTags.emplace_back("import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid/+esm'" + mermaidInit);
            }

        }

        MermaidScope::~MermaidScope() {}

        MermaidScope::MermaidScope(const MermaidScope &v) {}

        std::string MermaidScope::ScopeName() {
            return "mermaid";
        }

        std::vector<std::unique_ptr<::headless::runtime::CallArgument>> MermaidScope::BuildCallArguments() {
            std::vector<std::unique_ptr<::headless::runtime::CallArgument>> args;

            return args;
        }
    }
}

#endif //CHROMIUM_MERMAIDSCOPE_H
