create schema test;
create table test.points
(
    zoom_level integer,
    depth      double precision,
    geom       geometry,
    identifier serial not null
);

create unique index points_identifier_uindex
    on test.points (identifier);

create table test.polygons
(
    zoom_level integer,
    geom       geometry
);
create table test.calculation
(
    index_key  serial not null,
    payload    json   not null,
    calculated boolean default false
);

comment on table test.calculation is 'The data which is needed for background calculation';