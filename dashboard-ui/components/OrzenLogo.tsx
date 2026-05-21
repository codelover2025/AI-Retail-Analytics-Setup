import Image from "next/image";
import Link from "next/link";
import clsx from "clsx";

type Variant = "primary" | "icon";

const assets: Record<Variant, { src: string; width: number; height: number }> = {
  primary: {
    src: "/branding/orzen-logo-primary.png",
    width: 140,
    height: 40,
  },
  icon: {
    src: "/branding/orzen-icon.png",
    width: 32,
    height: 32,
  },
};

interface OrzenLogoProps {
  variant?: Variant;
  className?: string;
  href?: string;
  priority?: boolean;
}

export function OrzenLogo({
  variant = "primary",
  className,
  href = "/",
  priority = false,
}: OrzenLogoProps) {
  const { src, width, height } = assets[variant];

  const img = (
    <Image
      src={src}
      alt="Orzen"
      width={width}
      height={height}
      priority={priority}
      className={clsx("h-auto w-auto object-contain object-left", className)}
      style={{ maxHeight: variant === "primary" ? 36 : 28 }}
    />
  );

  if (!href) {
    return <div className="flex items-center">{img}</div>;
  }

  return (
    <Link
      href={href}
      className="flex items-center rounded-md focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
      aria-label="Orzen Vision home"
    >
      {img}
    </Link>
  );
}
