import React from "react";
import { LineWave } from "react-loader-spinner";

interface JSONBoxProps {
  loading: boolean;
  pyTorchImageResponseString: string;
}

/**
 * customFormatJSON to fix boxes being on too many lines.
 */
const customFormatJSON = (data: any): string => {
  if (
    data &&
    Array.isArray(data.scores) &&
    Array.isArray(data.classes) &&
    Array.isArray(data.boxes) &&
    Array.isArray(data.labels)
  ) {
    return `{
  "scores": ${JSON.stringify(data.scores, null, 2)},
  "classes": ${JSON.stringify(data.classes, null, 2)},
  "boxes": [
    ${data.boxes
      .map((inner: number[]) => `[ ${inner.join(", ")} ]`)
      .join(",\n    ")}
  ],
  "labels": ${JSON.stringify(data.labels, null, 2)}
}`;
  }
  return JSON.stringify(data, null, 2);
};

/**
 * applySyntaxHighlighting tokenizes a JSON string and wraps tokens in span tags,
 * so that keys, strings, numbers, booleans/null, and punctuation can be styled.
 */
const applySyntaxHighlighting = (jsonStr: string): string => {
  // Escape special HTML characters
  const escapeHTML = (str: string) =>
  str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const escaped = escapeHTML(jsonStr);
  const tokenRegex = /("(?:\\.|[^"\\])*")|(\b(?:true|false|null|[-+]?\d*\.?\d+)\b)|([\{\}\[\],:])/g;

  return escaped.replace(tokenRegex, (match, quoted, literal, punctuation, offset, fullStr) => {
    if (quoted !== undefined) {
      const after = fullStr.slice(offset + match.length).trimStart();
      if (after.startsWith(":")) {
        return `<span class="json-key">${match}</span>`;
      } else {
        return `<span class="json-string">${match}</span>`;
      }
    } else if (literal !== undefined) {
      // If literal looks like a number, apply number style; otherwise (true, false, null)
      if (/^[-+]?\d*\.?\d+$/.test(literal)) {
        return `<span class="json-number">${literal}</span>`;
      } else {
        return `<span class="json-boolean">${literal}</span>`;
      }
    } else if (punctuation !== undefined) {
      return `<span class="json-punctuation">${punctuation}</span>`;
    }
    return match;
  });
};

const JSONBox: React.FC<JSONBoxProps> = ({
  loading,
  pyTorchImageResponseString,
}) => {
  let parsedData: any;
  try {
    parsedData = JSON.parse(pyTorchImageResponseString);
  } catch (error) {
    parsedData = { error: "Invalid JSON" };
  }

  const formattedJSON = customFormatJSON(parsedData);
  const highlightedHTML = applySyntaxHighlighting(formattedJSON);
  const isJSONError = formattedJSON.includes("error")

  return (
    <div
      className={`text-left pl-4 h-full ${!loading ? "overflow-auto" : ""}`}
      style={{
        backgroundColor: "#272822",
        padding: "1rem",
      }}
    >
      {loading ? (
        <div className="w-full flex justify-center">
          <LineWave height="100" width="100" color="green" />
        </div>
      ) : (
        !isJSONError &&
        <pre
          style={{
            margin: 0,
            fontFamily: "monospace",
            fontSize: "0.9rem",
            whiteSpace: "pre-wrap",
          }}
          dangerouslySetInnerHTML={{ __html: highlightedHTML }}
        />
      )}
    </div>
  );
};

export default JSONBox;
