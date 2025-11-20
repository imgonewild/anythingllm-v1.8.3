import createDOMPurify from "dompurify";

const DOMPurify = createDOMPurify(window);
DOMPurify.setConfig({
  ADD_ATTR: ["target", "rel", "loading", "title"],
  ADD_TAGS: ["img"],
});

export default DOMPurify;
