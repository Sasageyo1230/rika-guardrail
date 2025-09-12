# Simple two-stage build for the stub (no runtime deps)

# 1) Build stage
FROM node:20-alpine AS build
WORKDIR /app
# Install pnpm (keeps future-proofing if you add deps later)
RUN npm install -g pnpm@8
# Bring in source
COPY package.json ./
COPY . .
# Build: copies src/index.js -> dist/index.js
RUN node scripts/build.mjs

# 2) Runtime stage
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
# Non-root user
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nodejs
# Bring only what we need to run
COPY --from=build /app/dist ./dist
COPY --from=build /app/package.json ./package.json
USER nodejs
EXPOSE 3000
CMD ["node", "dist/index.js"]
