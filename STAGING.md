# Staging Environment

## Railway Staging Setup

1. Create a separate Railway project for staging:
   ```bash
   railway login
   railway init --name goethe-booking-bot-staging
   ```

2. Link to deploy workflow branch (e.g., `develop`):
   ```bash
   railway link --project <staging-project-id>
   railway variables set AUTH_EMAIL=hamzarafiq655@gmail.com
   railway variables set AUTH_PASSWORD=<staging-password>
   railway up --detach
   ```

3. Add a staging deploy job to `.github/workflows/deploy.yml`:
   ```yaml
   deploy-staging:
     runs-on: ubuntu-latest
     if: github.ref == 'refs/heads/develop'
     steps:
       - uses: actions/checkout@v4
       - run: npm install -g @railway/cli
       - run: railway link --project <staging-project-id>
         env:
           RAILWAY_API_TOKEN: ${{ secrets.RAILWAY_API_TOKEN }}
       - run: railway up --detach
         env:
           RAILWAY_API_TOKEN: ${{ secrets.RAILWAY_API_TOKEN }}
   ```

## Netlify Staging Deploy

Netlify supports branch deploys out of the box:
- Push to `develop` → auto-deploys to `https://develop--goethe-booking-dashboard.netlify.app`
- Set in Netlify: Site settings → Build & deploy → Deploy contexts → `develop`

## Smoke Tests (Post-Deploy)

The `Smoke` workflow runs the smoke test suite after every push.
Before merging to `main`, verify staging passes all smoke tests.
