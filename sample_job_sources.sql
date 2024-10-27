-- Insert sample job sources for different regions
INSERT INTO job_sources (name, url, scraping_config) VALUES
('LinkedIn - Software Engineering', 
 'https://www.linkedin.com/jobs/search/?keywords=software%20engineer&location=United%20States',
 '{
     "type": "linkedin",
     "job_card_selector": ".jobs-search-results__list-item",
     "title_selector": "h3.base-search-card__title",
     "company_selector": ".base-search-card__subtitle",
     "location_selector": ".job-search-card__location"
 }'::jsonb),

('LinkedIn - Data Science', 
 'https://www.linkedin.com/jobs/search/?keywords=data%20scientist&location=United%20States',
 '{
     "type": "linkedin",
     "job_card_selector": ".jobs-search-results__list-item",
     "title_selector": "h3.base-search-card__title",
     "company_selector": ".base-search-card__subtitle",
     "location_selector": ".job-search-card__location"
 }'::jsonb),

('LinkedIn - Remote Tech', 
 'https://www.linkedin.com/jobs/search/?keywords=software%20engineer&f_WT=2',
 '{
     "type": "linkedin",
     "job_card_selector": ".jobs-search-results__list-item",
     "title_selector": "h3.base-search-card__title",
     "company_selector": ".base-search-card__subtitle",
     "location_selector": ".job-search-card__location"
 }'::jsonb);
