# Templates Data

This directory contains the data for the invitation templates. The templates are organized by plan category.

- `basic.ts`: Contains the templates for the Basic plan.
- `premium.ts`: Contains the templates for the Premium plan.
- `luxury.ts`: Contains the templates for the Luxury plan.
- `index.ts`: Exports all templates.

## Seeding the Database

The templates in this directory are not directly used by the application. Instead, they are seeded into the database using a seed script.

To seed the database with the templates, run the following command in the `apps/backend` directory:

```
npm run seed
```

This will populate the `Template` table in the database with the data from the files in this directory.
