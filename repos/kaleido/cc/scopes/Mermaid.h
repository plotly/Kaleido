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

        MermaidScope::MermaidScope()  {}

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
