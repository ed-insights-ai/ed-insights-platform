INSERT INTO schools (name, abbreviation, conference, mascot)
VALUES ('Ouachita Baptist', 'OBU', 'GAC', 'Tigers')
ON CONFLICT (abbreviation) DO NOTHING;
