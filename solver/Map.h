//
// Created by liu on 2020/3/7.
//

#ifndef MAPF_MAP_H
#define MAPF_MAP_H

#include <string>
#include <vector>

class Map {
public:
    enum class Direction {
        UP, RIGHT, DOWN, LEFT, NONE
    };

    static const Direction directions[4];
    static const int DIRECTION_X[4];
    static const int DIRECTION_Y[4];

private:
    size_t height = 0, width = 0;
    std::string type;
    std::vector<std::vector<char> > map;

    template<typename T>
    static void parseHeader(const std::string &line, const std::string &key, T &value);

public:
    explicit Map(const std::string &filename);

    auto getHeight() const { return this->height; };

    auto getWidth() const { return this->width; };

    const std::vector<char> &operator[](size_t index) const;

    std::pair<bool, std::pair<size_t, size_t>> getPosByDirection(std::pair<size_t, size_t> pos, Direction direction) const;
};


#endif //MAPF_MAP_H
