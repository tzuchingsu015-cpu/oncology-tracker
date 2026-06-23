create table if not exists articles (
  id           text not null,
  source_id    text not null,
  source_name  text not null,
  title        text not null,
  url          text not null,
  authors      text default '',
  abstract     text default '',
  period       text not null check (period in ('daily','weekly','monthly')),
  rank         int  not null,
  scraped_at   timestamptz not null default now(),
  primary key (id, period)
);

create index if not exists articles_period_scraped on articles(period, scraped_at desc);
create index if not exists articles_source_period  on articles(source_id, period);
