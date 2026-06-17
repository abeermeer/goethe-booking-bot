# Load test for Goethe Booking Bot API
# Requires k6: https://k6.io/docs/get-started/installation/
# Run: k6 run tests/k6_load.js

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

export const options = {
  stages: [
    { duration: '30s', target: 10 },   // ramp up to 10 users
    { duration: '1m', target: 20 },    // ramp up to 20 users
    { duration: '30s', target: 0 },    // ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% of requests under 500ms
    http_req_failed: ['rate<0.01'],    // less than 1% failure rate
  },
};

const BASE_URL = 'https://goethe-booking-bot-production-092f.up.railway.app/api/v1';
const FAILURE_RATE = new Rate('failed_requests');
const HEALTH_DURATION = new Trend('health_duration');

export default function () {
  // Health check
  const healthRes = http.get(`${BASE_URL}/health`);
  HEALTH_DURATION.add(healthRes.timings.duration);
  check(healthRes, {
    'health status is 200': (r) => r.status === 200,
    'health response is ok': (r) => r.json('status') === 'ok',
  });
  FAILURE_RATE.add(healthRes.status !== 200);

  // Login
  const loginRes = http.post(`${BASE_URL}/login`, JSON.stringify({
    email: 'hamzarafiq655@gmail.com',
    password: 'Hamza@123',
  }), { headers: { 'Content-Type': 'application/json' } });
  check(loginRes, {
    'login status is 200': (r) => r.status === 200,
    'login returns token': (r) => r.json('ok') === true,
  });
  FAILURE_RATE.add(loginRes.status !== 200);

  // Heartbeat (unauthenticated)
  const hbRes = http.get(`${BASE_URL}/heartbeat`);
  FAILURE_RATE.add(hbRes.status !== 200);

  sleep(1);
}
