(function (root, factory) {
  const api = factory();

  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }

  root.ResumeDiagnostics = api;
})(
  typeof globalThis !== "undefined" ? globalThis : this,
  function () {
    "use strict";

    const DEFAULT_MAX_TEXT = 80;
    const DEFAULT_MAX_OPTIONS = 4;

    function compactText(value) {
      return String(value ?? "")
        .replace(/\s+/g, " ")
        .trim();
    }

    function truncateText(value, maxLength = DEFAULT_MAX_TEXT) {
      const text = compactText(value);
      if (!text) return "";
      if (text.length <= maxLength) return text;
      return `${text.slice(0, Math.max(0, maxLength - 3))}...`;
    }

    function summarizeValue(value, { maxLength = DEFAULT_MAX_TEXT } = {}) {
      if (Array.isArray(value)) {
        const items = value
          .map((item) => compactText(item))
          .filter(Boolean)
          .slice(0, 3);

        if (items.length === 0) {
          return "(empty)";
        }

        const suffix = value.length > items.length ? ", ..." : "";
        return `"${truncateText(items.join(", ") + suffix, maxLength)}"`;
      }

      if (value && typeof value === "object") {
        try {
          return `"${truncateText(JSON.stringify(value), maxLength)}"`;
        } catch (_) {
          return '"[object]"';
        }
      }

      const text = truncateText(value, maxLength);
      return text ? `"${text}"` : "(empty)";
    }

    function summarizePrivateValue(value) {
      if (value === null || value === undefined || value === "") {
        return "(empty)";
      }
      if (Array.isArray(value)) {
        return value.length ? "[redacted:array]" : "(empty)";
      }
      if (typeof value === "object") {
        return Object.keys(value).length ? "[redacted:object]" : "(empty)";
      }
      return `[redacted:${typeof value}]`;
    }

    function sanitizeDiagnosticText(value) {
      return compactText(value)
        .replace(/[1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[0-9Xx]/g, "[redacted:id]")
        .replace(/(?<!\d)1[3-9]\d{9}(?!\d)/g, "[redacted:phone]")
        .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, "[redacted:email]")
        .replace(/([?&](?:access_)?token=)[^&#\s]+/gi, "$1[redacted]");
    }

    function summarizeDiagnosticDetail(value) {
      return summarizeValue(sanitizeDiagnosticText(value));
    }

    function summarizeOptions(options, { maxItems = DEFAULT_MAX_OPTIONS } = {}) {
      const list = Array.isArray(options)
        ? options.map((item) => truncateText(item, 24)).filter(Boolean)
        : [];

      if (list.length === 0) {
        return "[]";
      }

      const visible = list.slice(0, maxItems).join(" | ");
      const suffix = list.length > maxItems ? " | ..." : "";
      return `[${visible}${suffix}]`;
    }

    function formatTransform(transform) {
      if (!transform || typeof transform !== "object") {
        return "none";
      }

      const type = compactText(transform.type) || "none";
      if (type === "date_part" || type === "phone_part") {
        const part = compactText(transform.part);
        return part ? `${type}(${part})` : type;
      }

      if (type === "boolean_choice") {
        return `${type}(${compactText(transform.trueValue) || "true"}/${compactText(
          transform.falseValue
        ) || "false"})`;
      }

      if (type === "join") {
        return `${type}(${compactText(transform.separator) || ","})`;
      }

      return type;
    }

    function formatFieldSummary(field) {
      return [
        "[扫描]",
        compactText(field?.fieldId) || "(no-field-id)",
        compactText(field?.kind) || "unknown",
        `label=${summarizeValue(field?.label)}`,
        `name=${summarizeValue(field?.name)}`,
        `id=${summarizeValue(field?.id)}`,
        `placeholder=${summarizeValue(field?.placeholder)}`,
        `section=${summarizeValue(field?.sectionLabel)}`,
        `nearby=${summarizeOptions(field?.nearbyLabels)}`,
        `options=${summarizeOptions(field?.options)}`,
        `context=${summarizeValue(field?.context, { maxLength: 120 })}`,
      ].join(" ");
    }

    function formatMappingSummary(field, mapping, { source = "ai" } = {}) {
      return [
        `[映射:${compactText(source) || "ai"}]`,
        compactText(field?.fieldId) || "(no-field-id)",
        `${summarizeValue(field?.label)} -> ${
          compactText(mapping?.resumePath) || "(unmapped)"
        }`,
        `transform=${formatTransform(mapping?.transform)}`,
        `reason=${summarizeValue(mapping?.reason, { maxLength: 120 })}`,
      ].join(" ");
    }

    function formatValueSummary(field, mapping, rawValue, finalValue) {
      return [
        "[取值]",
        compactText(field?.fieldId) || "(no-field-id)",
        compactText(mapping?.resumePath) || "(unmapped)",
        `raw=${summarizePrivateValue(rawValue)}`,
        `final=${summarizePrivateValue(finalValue)}`,
      ].join(" ");
    }

    function formatSkipSummary(field, mapping, detail, rawValue, finalValue) {
      return [
        "[跳过]",
        compactText(field?.fieldId) || "(no-field-id)",
        `${summarizeValue(field?.label)} -> ${
          compactText(mapping?.resumePath) || "(unmapped)"
        }`,
        `raw=${summarizePrivateValue(rawValue)}`,
        `final=${summarizePrivateValue(finalValue)}`,
        `detail=${summarizeDiagnosticDetail(detail)}`,
      ].join(" ");
    }

    function formatFillSummary({
      field,
      mapping,
      rawValue,
      finalValue,
      fillResult,
    }) {
      const status = fillResult?.filled ? "成功" : "失败";
      return [
        `[填充:${status}]`,
        compactText(field?.fieldId) || "(no-field-id)",
        `${summarizeValue(field?.label)} -> ${
          compactText(mapping?.resumePath) || "(unmapped)"
        }`,
        `raw=${summarizePrivateValue(rawValue)}`,
        `final=${summarizePrivateValue(finalValue)}`,
        `detail=${summarizeDiagnosticDetail(fillResult?.message)}`,
      ].join(" ");
    }

    return {
      formatFieldSummary,
      formatMappingSummary,
      formatValueSummary,
      formatSkipSummary,
      formatFillSummary,
      formatTransform,
      summarizeValue,
      summarizePrivateValue,
      sanitizeDiagnosticText,
      summarizeOptions,
      truncateText,
    };
  }
);
