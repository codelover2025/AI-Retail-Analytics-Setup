import { NextRequest, NextResponse } from "next/server";

/**
 * Next.js Edge Middleware — route protection.
 *
 * Public routes: /login, /_next/*, /api/* (backend proxy), /branding/*, /favicon*
 * All other routes require a valid JWT in localStorage (checked via cookie mirror).
 *
 * Strategy: The AuthProvider stores the token in localStorage AND writes a
 * lightweight JS-readable cookie `orzen_auth=1` so middleware can gate
 * server-side without exposing the token to middleware (which cannot read LS).
 *
 * This provides UX-level protection (redirect to /login on hard navigation).
 * API-level protection is enforced by the FastAPI backend independently.
 */

const PUBLIC_PATHS = [
  "/login",
  "/_next",
  "/favicon",
  "/branding",
  "/backend-api",
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow all public paths
  const isPublic = PUBLIC_PATHS.some((p) => pathname.startsWith(p));
  if (isPublic) return NextResponse.next();

  // Check for auth presence cookie (set by AuthProvider on login)
  const authCookie = request.cookies.get("orzen_auth");
  if (!authCookie || authCookie.value !== "1") {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  // Run on all routes except static files and API
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|branding|backend-api).*)",
  ],
};
