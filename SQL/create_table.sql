create schema test;
create table test.points
(
    zoom_level integer,
    depth      double precision,
    geom       geometry
);

create table test.polygons
(
    zoom_level integer,
    geom       geometry
);