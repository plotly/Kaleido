//
// Created by jmmease on 6/17/20.
//
#include "BaseScope.h"
#include "base/bind.h"
#include "base/command_line.h"
#include "base/strings/string_util.h"
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
    // Add MathJax config
    scriptTags.emplace_back("window.PlotlyConfig = {MathJaxConfig: 'local'}");

    // Process plotlyjs
    if (HasCommandLineSwitch("plotlyjs")) {
        std::string plotlyjsArg = GetCommandLineSwitch("plotlyjs");

        // Check if value is a URL
        GURL plotlyjsUrl(plotlyjsArg);
        if (plotlyjsUrl.is_valid()) {
            scriptTags.push_back(plotlyjsArg);
        } else {
            // Check if this is a local file path
            if (std::ifstream(plotlyjsArg)) {
                localScriptFiles.emplace_back(plotlyjsArg);
            } else {
                std::cerr << "--plotlyjs argument skipped since it is not a valid URL: " << plotlyjsArg;
                scriptTags.emplace_back("https://cdn.plot.ly/plotly-latest.min.js");
            }
        }
    } else {
        scriptTags.emplace_back("https://cdn.plot.ly/plotly-latest.min.js");
    }

    // MathJax
    if (HasCommandLineSwitch("mathjax")) {
        std::string mathjaxArg = GetCommandLineSwitch("mathjax");

        GURL mathjaxUrl(mathjaxArg);
        if (mathjaxUrl.is_valid()) {
            std::stringstream mathjaxStringStream;
            mathjaxStringStream << mathjaxArg << "?config=TeX-AMS-MML_SVG";
            scriptTags.push_back(mathjaxStringStream.str());
        } else {
            std::cerr << "--mathjax argument skipped since it is not a valid URL: " << mathjaxArg;
        }
    }

    // Topojson
    if (HasCommandLineSwitch("topojson")) {
        std::string topojsonArg = GetCommandLineSwitch("topojson");
        if (GURL(topojsonArg).is_valid()) {
            topojsonUrl = topojsonArg;
        } else {
            std::cerr << "--topojson argument skipped since it is not a valid URL: " << topojsonArg;
        }
    }

    // Process mapbox-token
    if (HasCommandLineSwitch("mapbox-access-token")) {
        mapboxToken = GetCommandLineSwitch("mapbox-access-token");
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
