//
// Created by jmmease on 6/17/20.
//
#include "BaseScope.h"
#include "base/bind.h"
#include "base/command_line.h"
#include "headless/public/devtools/domains/runtime.h"

#include <streambuf>
#include <string>
#include <sstream>
#include <iostream>
#include <fstream>

#ifndef CHROMIUM_PLOTLY_H
#define CHROMIUM_PLOTLY_H


class Plotly: public BaseScope {
public:
    Plotly();
    ~Plotly() override;
    Plotly(const Plotly &v);

    std::string PluginName() override;
    std::vector<std::unique_ptr<::headless::runtime::CallArgument>> BuildCallArguments() override;

public:
    std::string topojsonUrl;
    std::string mapboxToken;
};


Plotly::Plotly(): topojsonUrl(), mapboxToken() {
    // Get command line options
    base::CommandLine *commandLine = base::CommandLine::ForCurrentProcess();

    // Add MathJax config
    scriptTags.emplace_back("window.PlotlyConfig = {MathJaxConfig: 'local'}");

    // Process plotlyjs
    if (commandLine->HasSwitch("plotlyjs")) {
        std::string plotlyjs_arg = commandLine->GetSwitchValueASCII("plotlyjs");
        // Check if value is a URL
        GURL plotlyjs_url(plotlyjs_arg);
        if (plotlyjs_url.is_valid()) {
            scriptTags.push_back(plotlyjs_arg);
        } else {
            // Check if this is a local file path
            if (std::ifstream(plotlyjs_arg)) {
                localScriptFiles.emplace_back(plotlyjs_arg);
            } else {
                scriptTags.emplace_back("https://cdn.plot.ly/plotly-latest.min.js");
            }
        }
    } else {
        scriptTags.emplace_back("https://cdn.plot.ly/plotly-latest.min.js");
    }

    // MathJax
    if (commandLine->HasSwitch("mathjax")) {
        std::string mathjax_arg = commandLine->GetSwitchValueASCII("mathjax");
        GURL mathjax_url(mathjax_arg);

        if (mathjax_url.is_valid()) {
            std::stringstream mathjaxStringStream;
            mathjaxStringStream << mathjax_arg << "?config=TeX-AMS-MML_SVG";
            scriptTags.push_back(mathjaxStringStream.str());
        }
    }

    // Topojson
    if (commandLine->HasSwitch("topojson")) {
        std::string topojsonArg = commandLine->GetSwitchValueASCII("topojson");
        if (GURL(topojsonArg).is_valid()) {
            topojsonUrl = topojsonArg;
        }
    }

    // Process mapbox-token
    if (commandLine->HasSwitch("mapbox-access-token")) {
        mapboxToken = commandLine->GetSwitchValueASCII("mapbox-access-token");
    }

    // Additional initialization scripts (these must be added after plotly.js)
    localScriptFiles.emplace_back("./js/kaleido_scopes.js");
}

Plotly::~Plotly() {}

Plotly::Plotly(const Plotly &v): topojsonUrl(v.topojsonUrl), mapboxToken(v.mapboxToken) {}

std::string Plotly::PluginName() {
    return "plotly";
}

std::vector<std::unique_ptr<::headless::runtime::CallArgument>> Plotly::BuildCallArguments() {
    std::vector<std::unique_ptr<::headless::runtime::CallArgument>> args;

    // Add mapbox token from command line
    args.push_back(
            headless::runtime::CallArgument::Builder()
                    .SetValue(std::make_unique<base::Value>(base::StringPiece(mapboxToken)))
                    .Build()
    );

    // Add topojson url from command-line
    args.push_back(
            headless::runtime::CallArgument::Builder()
                    .SetValue(std::make_unique<base::Value>(base::StringPiece(topojsonUrl)))
                    .Build()
    );
    return args;
}

#endif //CHROMIUM_PLOTLY_H
