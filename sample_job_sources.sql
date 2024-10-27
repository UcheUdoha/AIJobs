-- Insert sample job sources for different regions
INSERT INTO job_sources (name, url, scraping_config) VALUES
('Indeed - Global Software Jobs', 
 'https://www.indeed.com/worldwide',
 '{
     "type": "indeed",
     "job_card_selector": "div.job_seen_beacon",
     "title_selector": "h2.jobTitle",
     "company_selector": "span.companyName",
     "location_selector": "div.companyLocation"
 }'::jsonb),

('LinkedIn - Global Tech', 
 'https://www.linkedin.com/jobs/search/?keywords=software%20developer',
 '{
     "type": "linkedin",
     "job_card_selector": "div.base-card",
     "title_selector": "h3.base-search-card__title",
     "company_selector": "h4.base-search-card__subtitle",
     "location_selector": "span.job-search-card__location"
 }'::jsonb),

('Indeed - Europe Tech', 
 'https://www.indeed.com/jobs?q=software+developer&l=Europe',
 '{
     "type": "indeed",
     "job_card_selector": "div.job_seen_beacon",
     "title_selector": "h2.jobTitle",
     "company_selector": "span.companyName",
     "location_selector": "div.companyLocation"
 }'::jsonb),

('LinkedIn - APAC Region', 
 'https://www.linkedin.com/jobs/search/?keywords=software%20engineer&location=Asia%20Pacific',
 '{
     "type": "linkedin",
     "job_card_selector": "div.base-card",
     "title_selector": "h3.base-search-card__title",
     "company_selector": "h4.base-search-card__subtitle",
     "location_selector": "span.job-search-card__location"
 }'::jsonb),

('Remote Tech Jobs', 
 'https://www.linkedin.com/jobs/search/?keywords=software%20engineer&location=Remote',
 '{
     "type": "linkedin",
     "job_card_selector": "div.base-card",
     "title_selector": "h3.base-search-card__title",
     "company_selector": "h4.base-search-card__subtitle",
     "location_selector": "span.job-search-card__location"
 }'::jsonb);
