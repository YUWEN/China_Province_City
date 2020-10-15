# 使用selenium+chrome_driver实现可视化数据抓取
民政部网站获取最新行政区划代码并保存在数据库中

# 民政部网站
http://www.mca.gov.cn/article/sj/xzqh/


# 注意：
使用前需下载Chrome插件，并替换代码中执行插件的文件位置


# mysql 建表和查询语句
建表

  create table version (id int primary key auto_increment, url varchar(200) not null,check_time datetime default now());
  
  create table province (id int primary key auto_increment,code varchar(20) not null,title varchar(32) not null);
  
  create table city (id int primary key auto_increment,code varchar(20) not null,title varchar(32) not null,pro_code varchar(20));
  
  create table county (id int primary key auto_increment,code varchar(20) not null,title varchar(32) not null,ci_code varchar(20),pro_code varchar(20));
  
连表查询

  select county.title,city.title,province.title from county inner join city on city.code=county.ci_code inner join province on province.code=city.pro_code;
  
  
# PS
代码为本人自学python中练习代码，肯定存在很多问题，不喜勿喷，希望大家共同进步，头发越来越多...
  
