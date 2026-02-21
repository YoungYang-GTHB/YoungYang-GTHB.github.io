import type { PersonalInfo } from '@/types/resume';

interface Props {
  data: PersonalInfo;
}

export function JsonLd({ data }: Props) {
  const schemaData = {
    "@context": "https://schema.org",
    "@type": "Person",
    "name": data.name,
    "jobTitle": data.title,
    "description": data.summary.trim(),
    "email": `mailto:${data.email}`,
    "telephone": data.phone,
    "address": {
      "@type": "PostalAddress",
      "addressLocality": data.location,
    },
    "url": data.github || data.linkedin,
    "sameAs": [data.github, data.linkedin].filter(Boolean),
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schemaData) }}
    />
  );
}
