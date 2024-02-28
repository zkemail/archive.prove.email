import { RateLimiterMemory } from "rate-limiter-flexible";

export const rateLimiter = new RateLimiterMemory({
	points: 50,
	duration: 10
});
