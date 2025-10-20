CREATE DATABASE HOTEL_RESERVATION CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE HOTEL_RESERVATION;
-- user
CREATE TABLE USERS(
ID INT auto_increment PRIMARY KEY,
EMAIL VARCHAR(255) NOT NULL unique,
PASSWARD_HASH varchar(255) NOT NULL,
FULL_NAME VARCHAR(255),
PHONE INT,
ROLE ENUM('CUSTOMER','ADMIN') DEFAULT 'CUSTOMER',
CREATED_AT TIMESTAMP DEFAULT current_timestamp,
UPDATED_AT timestamp default current_timestamp on update current_timestamp
) engine=InnoDB;
-- hotels
create table hotels (
id int auto_increment primary key,
name varchar(30) not null,
address text,
city varchar(30),
star_rating tinyint, 
created_at timestamp default current_timestamp
) engine=innodb;
-- room types
create table room_types(
id int auto_increment primary key,
hotel_id int not null,
name varchar(30) not null,
description text,
base_price decimal(10,2)not null,
capacity tinyint not null,
total_count int not null default 0,
create_at timestamp default current_timestamp,
foreign key(hotel_id) references hotels(id) on delete cascade
)engine=InnoDB;
-- Room inventory(optional per-day availlability for dynamic pricing)
create table room_inventory(
id int auto_increment primary key,
room_type_id int not null unique key,
date date not null unique key,
avilability_count int not null,
price_override decimal(10,2), -- season price override
foreign key (room_type_id) references room_types(id) on delete cascade
)engine=innodb;
-- Bookings
create table bookings(
id bigint auto_increment primary key,
user_id int not null,
hotel_id int not null,
status enum('pending','confirmed','cancelled','checking_in','checking_out') default 'pending',
total_amount decimal(10,2) not null,
curreny varchar(8) default 'INR',
created_at timestamp default current_timestamp,
updated_at timestamp default current_timestamp on update current_timestamp,
checkin_date date not null,
checkout_date date not null,
foreign key(user_id) references users(id),
foreign key(hotel_id) references hotels(id)
)engine=InnoDB;
-- Booking items
create table booking_item(
id bigint auto_increment primary key,
booking_id bigint not null,
room_type_id int not null,
quantity int not null,
price_per_room decimal(10,2) not null,
foreign key (booking_id) references  bookings(id) on delete cascade,
foreign key(room_type_id) references room_types(id)
) engine=InnoDB;
-- Payments
create table payment(
id bigint auto_increment primary key,
booking_id bigint not null,
amount decimal(12,2) not null,
method enum('card','netbanking','upi','offline') default 'card',
status enum('initiated','success','failed','refunded'),
txn_refernce varchar(50),
created_at timestamp default current_timestamp,
foreign key (booking_id) references bookings(id) on delete cascade
)engine=innodb;
-- Coupans
create table coupons(
id int auto_increment primary key,
code varchar(50) unique not null,
description text,
discount_type enum('percentage','flat') not null,
discount_value decimal(10,2) not null,
valid_from date,
valid_to date,
min_amount decimal(12,2) default 0,
max_uses int default 0,
used_count int default 0
)engine=InnoDB;
-- Audit Logs
create table audit_log(
id bigint auto_increment primary key,
entity varchar(50),
entity_id bigint ,
action varchar(50),
performed_by int,
details json,
created_at timestamp default current_timestamp
) engine=innodb;
-- Indexes for column queries
create index idx_roomtype_hotel on room_types(hotel_id);
create index idx_inventory_date on room_inventory(date);
create index idx_booking_user on bookings(user_id);
create index idx_booking_dates on bookings(checkin_date,checkout_date);

-- Availability per room_type
select rt.id as room_type_id,rt.name,rt.total_count - ifnull(sum(bi.quantity),0) as available
from room_types rt
left join booking_item bi
on bi.room_type_id=rt.id
left join bookings b
on b.id=bi.booking_id
and b.status in ('pending','confirmed')
and not (b.checkout_date <='2025-10-10' or b.checkin_date >='2025-10-13') 
where rt.hotel_id=1
group by rt.id;




 

