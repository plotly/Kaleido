//
// Created by jmmease on 6/23/20.
//

#include <iostream>

#ifndef CHROMIUM_UTILS_H
#define CHROMIUM_UTILS_H

namespace kaleido {
    namespace utils {
        void writeJsonMessage(int code, std::string message) {
            std::string error = base::StringPrintf(
                    "{\"code\": %d, \"message\": \"%s\", \"result\": null}\n",
                    code, message.c_str());
            std::cout << error;
        }
    }
}

#endif //CHROMIUM_UTILS_H
