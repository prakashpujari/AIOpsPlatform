# ─────────────────────────────────────────────
# Multi-stage Dockerfile — Next.js Frontend
# ─────────────────────────────────────────────

FROM node:20-alpine AS base
ENV NODE_ENV=production
WORKDIR /app
RUN apk add --no-cache libc6-compat

FROM base AS deps
COPY package.json package-lock.json* ./
RUN npm ci --only=production

FROM base AS dev-deps
COPY package.json package-lock.json* ./
RUN npm ci

FROM dev-deps AS builder
COPY . .
RUN npm run build

FROM base AS development
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

FROM base AS production
COPY --from=deps /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY package.json ./

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs && \
    chown -R nextjs:nodejs /app
USER nextjs

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:3000/api/health || exit 1
CMD ["node", "node_modules/.bin/next", "start"]
